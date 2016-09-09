"""
TIM'S FREE IMPROVISER
Written in Python 3.5.1

The goal of this project is to receive information that has been extracted from real-time monophonic audio and output similar information for use with a software synthesizer.
These kinds of information are currently:
-pitch
-density of notes
-MFCC (for the purpose of approximating timbre) 

Future features:
-Determine melodic motifs/patterns from input and incorporate them into output
-Develop output stream that motifs can be incorporated into
-Actually ouput the data over OSC
-Possibly develop a fixed compositional framework for the improvisation

Bibliography:
-python-osc: https://pypi.python.org/pypi/python-osc
-music21: http://web.mit.edu/music21/doc/

MIT License (c) Tim Bedford
"""

import argparse
import math
from random import randint
from pythonosc import dispatcher
from pythonosc import osc_server
from music21 import *

notegroup = []
phraselist = []
denselist = []

def printCurrentNote(unused_addr, args, note):
    """ Prints incoming notes as they are received """
    print("[{0}] ~ {1}".format(args[0], note))

def updatePhraseList(unused_addr, args, note, time):
    """
    -Receives note and time since previous note
    -Divides series of notes into phrases and appends phrases to list
    -Very crude method of dividing phrases
    """
    global notegroup
    global phraselist
    if time < 800: #800 milliseconds is an arbitrary number
        notegroup.append(note)
    else:
        strm = phraseToStream(notegroup)
        print(keyOfPhrase(strm))
        phraselist.append(notegroup)
        notegroup = []

def updateDensityList(unused_addr, args, density):
    """
    -Receives the note density at a regular interval of time
    -Appends the value to a global list variable
    -Interval is set in Max/MSP
    """
    global denselist
    denselist.append(density)

def keyOfPhrase(p):
    """ Determines key of phrase """
    key = p.analyze('key')
    return [key.tonic.name, key.mode]
              
def phraseToStream(nums):
    stream1 = stream.Stream()
    for i in nums:
        stream1.append(note.Note(midiNumToNote(i)))
    return stream1

def midiNumToNote(i):
    x = pitch.Pitch()
    x.midi = i
    print(x.nameWithOctave)
    return x.nameWithOctave

def randomTranspose(p):
    """ Transposes phrase by random interval """
    return p.transpose(randint(1,12))

def pitchRange(p):
    """ Finds range between highest and lowest pitch in phrase """
    fe = features.jSymbolic.RangeFeature(p)
    return fe.extract().vector[0]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port",
                        type=int, default=5005, help="The port to listen on")
    args = parser.parse_args()
    #Dispatcher "listens" on these addresses and sends any matching information
    #to the designated function
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/space", updatePhraseList, "space")
    dispatcher.map("/density", updateDensityList, "density")
    dispatcher.map("/note", printCurrentNote, "note")

    #Launches the server and continues to run until manually ended
    server = osc_server.ThreadingOSCUDPServer(
        (args.ip, args.port), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()
