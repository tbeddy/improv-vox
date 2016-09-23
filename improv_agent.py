"""
TIM'S FREE IMPROVISER
Written in Python 3.5.1

The goal of this project is to receive information that has been extracted 
from real-time monophonic audio and output similar information for use with 
a software synthesizer.

Information is received as a series of values that describe a note.
For the current version of this protocol (0.1), these are:
-pitch/frequency (float) (in range of 50.0 to 400.0)
-duration in milliseconds (int)
-velocity (int)
-MFCC (four floats)

Future features:
-Determine melodic motifs/patterns from input and incorporate them into output
-Develop output stream that motifs can be incorporated into
-Actually ouput the data over OSC
-Possibly develop a fixed compositional framework for the improvisation

MIT License (c) Tim Bedford
"""

import argparse
import math
from copy import deepcopy
from random import randint
from music21 import *
from pythonosc import dispatcher, osc_server, osc_message_builder, udp_client
from note_class import MyNote

input_OSC_port = 5005
output_OSC_port = 6006

#This section is to establish the "client" (the part of the program sending
#OSC data). It will be reorganized soon, since all of these variables
#probably shouldn't be global.
output_parser = argparse.ArgumentParser()
output_parser.add_argument("--ip", default="127.0.0.1", help="The ip of the OSC server")
output_parser.add_argument("--port", type=int, default=output_OSC_port ,help="The port the OSC server is listening on")
output_args = output_parser.parse_args()     
client = udp_client.UDPClient(output_args.ip, output_args.port)

#All notes played by the program and phrases derived from these notes
comp_all_notes = []
comp_phrases = []

#All notes played by the human and phrases derived from these notes
human_all_notes = []
human_phrases = []

def storeNewNote(unused_addr, args, pitch, duration, velocity, c1, c2, c3, c4):
    """
    -Stores incoming notes in as they are received
    -Receives notes as series of seven parameters:
       -pitch
       -note duration
       -velocity
       -four coefficients derived from the mel-frequency cepstrum of the signal
    """
    global human_all_notes
    new_note = MyNote(pitch, duration, velocity, c1, c2, c3, c4)
    human_all_notes.append(new_note)
    sendNote(new_note) #try sending a note; should not be in final function
    
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
    return x.nameWithOctave

def pitchRange(p):
    """ Finds range between highest and lowest pitch in phrase """
    fe = features.jSymbolic.RangeFeature(p)
    return fe.extract().vector[0]

#~~~~~~~~~~~~~~~~~~~~~~~~Generative Functions~~~~~~~~~~~~~~~~~~~~~~
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
    new_phrase = stream.Stream()
    for i in range(len(phrase)-1, -1, -1):
        new_phrase.append(phrase[i]) #use the music21 insert function, not Python insert
    return new_phrase

def transpose(phrase, interval):
    """
    -Raises every note in phrase by designated interval
    -Only alters frequency/pitch parameter
    """
    new_phrase = stream.Stream()
    for note in phrase:
        new_phrase.append(note.transpose(interval))
    return new_phrase

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
    new_phrase = stream.Stream()
    for note in phrase:
        dur = note.duration.quarterLength
        n = note #make a copy of the note
        n.duration = duration.Duration(degree * dur)
        new_phrase.append(n)
    return new_phrase

def make_phrase_outoftune(phrase, note_num):
    """
    -Randomly alters a few notes in a phrase to make them offkey
    """

def make_note_intune(note1):
    """
    -Assigns any offkey notes to nearest note
    -If note is closer to neighboring note instead
    -Ex: C5 (30 cents) becomes C5 (0 cents)
         C5 (70 cents) becomes C#5 (0 cents)
         C5 (-30 cents) becomes C5 (0 cents)
         C5 (-70 cents) becomes B4 (0 cents)
    """
    note2 = deepcopy(note1)
    note2.pitch.microtone = 0
    if (note1.pitch.microtone.cents >= 50):
        note2 = note2.transpose(1)     
    elif (note1.pitch.microtone.cents <= -50):
        note2 = note2.transpose(-1)
    return note2

def make_phrase_inkey(phrase):
    """
    -Applies the make_note_intune function to all notes in a phrase
    """
    new_phrase = stream.Stream()
    for note in phrase:
        new_phrase.append(make_note_intune(note))
    return new_phrase

def add_flourish(phrase):
    """
    -Adds at least one note to a phrase  
    """

#~~~~~~~~~~~~~~~~~~~~~OSC Sending~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def sendNote(this_note):
    """
    -Sends each of the parameters of a note as an OSC message
    """
    msg = osc_message_builder.OscMessageBuilder(address = "/note")
    msg.add_arg(this_note.pitch)
    msg.add_arg(this_note.duration)
    msg.add_arg(this_note.velocity)
    msg.add_arg(this_note.mfcc[0])
    msg.add_arg(this_note.mfcc[1])
    msg.add_arg(this_note.mfcc[2])
    msg.add_arg(this_note.mfcc[3])
    msg = msg.build()
    client.send(msg)
    
#~~~~~~~~~~~~~~~~~~~~~OSC Messaging~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#This section is for receiving OSC messages and sending new OSC messages.

if __name__ == "__main__":
    input_parser = argparse.ArgumentParser()
    input_parser.add_argument("--ip",
                        default="127.0.0.1", help="The ip to listen on")
    input_parser.add_argument("--port",
                        type=int, default=input_OSC_port, help="The port to listen on")
    input_args = input_parser.parse_args()
    #Dispatcher "listens" on these addresses and sends any matching information
    #to the designated function
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/note", storeNewNote, "note")

    #Launches the server and continues to run until manually ended
    server = osc_server.ThreadingOSCUDPServer(
        (input_args.ip, input_args.port), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()
