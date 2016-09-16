"""
TIM'S FREE IMPROVISER
Written in Python 3.5.1

The goal of this project is to receive information that has been extracted 
from real-time monophonic audio and output similar information for use with 
a software synthesizer.

Information is received as a series of values that describe a note.
For the current version of this protocol (0.1), these are:
-pitch
-duration
-velocity
-MFCC

Future features:
-Determine melodic motifs/patterns from input and incorporate them into output
-Develop output stream that motifs can be incorporated into
-Actually ouput the data over OSC
-Possibly develop a fixed compositional framework for the improvisation
-Series of functions for transforming individual phrases

MIT License (c) Tim Bedford
"""

import argparse
import math
from random import randint
from pythonosc import dispatcher
from pythonosc import osc_server
from music21 import *

#All notes played by the program and phrases derived from these notes
comp_all_notes = []
comp_phrases = []

#All notes played by the human and phrases derived from these notes
human_all_notes = []
human_phrases = []

def storeNewNote(unused_addr, args, pitch, note_duration, velocity, c1, c2, c3, c4):
    """
    -Stores incoming notes in as they are received
    -Receives notes as series of seven parameters:
       -pitch
       -note duration
       -velocity
       -four coefficients derived from the mel-frequency cepstrum of the signal
    """
    global human_all_notes
    new_note = note.Note()
    new_note.duration = duration.Duration(1) #not using the duration input yet; will fix
    new_note.volume.velocity = velocity
    #not sure how to append my MFCC data to my notes yet
    print(new_note)
    human_all_notes.append(new_note)
    
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

def pitchRange(p):
    """ Finds range between highest and lowest pitch in phrase """
    fe = features.jSymbolic.RangeFeature(p)
    return fe.extract().vector[0]

#Generative Functions~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#These functions are for the purpose of generating new material.

def generate_phrase():
    """
    -Creates initial phrase for f
    -Should have no relation to anything the vocalist is doing
    -First creative decision from f
    """
    thephrase = stream.Stream()
    phrase_length = randint(1, 8) #random length for phrase
    for i in range(phraselist): #generate several notes and append each to the stream
        current_note = note.Note() #blank instance of note

def permutate_phrase(phrase):
    """
    This function will reference several other functions that use established
    methods to permutate (AKA in some way alter) a phrase.
    """

def retrograde(phrase):
    """
    -Reverses order of notes in phrase
    -Does not alter any of notes' parameters
    """

def transpose(phrase, interval):
    """
    -Raises every note in phrase by designated interval
    -Only alters frequency/pitch parameter
    """

def invert(phrase):
    """
    -Starts on intial note
    -Next note is inversion of interval
    -Ex: C4 to E4 (4 semitones) becomes C4 to G#3 (-4 semitones)
    -Only alters frequency/pitch parameter (and not for first note)
    """

def stretch(phrase, degree):
    """
    -Stretches (or shrinks) phrase duration
    -Equally stretches each note
    -Use float between 0.0 and 1.0 to shrink
    -Only alters duration parameter
    """

def make_offkey(phrase, note_num):
    """
    -Randomly alters a few notes in a phrase to make them offkey
    """

def make_inkey(phrase):
    """
    -Assigns any offkey notes to nearest note
    """

#OSC Messaging~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#This section is for receiving OSC messages and sending new OSC messages.

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
    dispatcher.map("/note", storeNewNote, "note")

    #Launches the server and continues to run until manually ended
    server = osc_server.ThreadingOSCUDPServer(
        (args.ip, args.port), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()
